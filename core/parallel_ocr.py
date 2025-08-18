"""
並列OCR処理モジュール
複数のPDFファイルを並列処理して高速化
"""

import asyncio
import concurrent.futures
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading
from queue import Queue

from core.config import get_config
from core.text_engine import TextEngine

logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """処理ステータス"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OCRTask:
    """OCRタスク"""
    file_path: Path
    task_id: str
    status: ProcessingStatus = ProcessingStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        """処理時間を取得"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class ParallelOCRProcessor:
    """並列OCR処理クラス"""
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        初期化
        
        Args:
            max_workers: 最大ワーカー数（省略時は設定から取得）
        """
        self.config = get_config()
        self.max_workers = max_workers or self.config.processing.max_workers
        self.text_engine = TextEngine(self.config)
        
        # タスク管理
        self.tasks: Dict[str, OCRTask] = {}
        self.task_queue = Queue()
        self.results_queue = Queue()
        
        # 進捗コールバック
        self.progress_callbacks: List[Callable] = []
        
        # 統計情報
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'total_duration': 0.0,
            'average_duration': 0.0
        }
    
    def add_progress_callback(self, callback: Callable[[OCRTask], None]):
        """
        進捗コールバックを追加
        
        Args:
            callback: タスク状態変更時に呼ばれる関数
        """
        self.progress_callbacks.append(callback)
    
    def _notify_progress(self, task: OCRTask):
        """進捗を通知"""
        for callback in self.progress_callbacks:
            try:
                callback(task)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    def process_files_parallel(
        self,
        file_paths: List[Path],
        ocr_function: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        複数ファイルを並列処理（同期版）
        
        Args:
            file_paths: 処理するファイルパスのリスト
            ocr_function: OCR処理関数（省略時はデフォルト使用）
            
        Returns:
            処理結果のリスト
        """
        if not file_paths:
            return []
        
        # OCR関数の設定
        if ocr_function is None:
            ocr_function = self._default_ocr_function
        
        # タスクを作成
        tasks = []
        for i, file_path in enumerate(file_paths):
            task = OCRTask(
                file_path=file_path,
                task_id=f"task_{i}_{file_path.name}"
            )
            self.tasks[task.task_id] = task
            tasks.append(task)
        
        self.stats['total_tasks'] = len(tasks)
        
        # ThreadPoolExecutorで並列処理
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # タスクを submit
            future_to_task = {
                executor.submit(self._process_single_file, task, ocr_function): task
                for task in tasks
            }
            
            # 完了を待つ
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Task {task.task_id} failed: {e}")
                    task.status = ProcessingStatus.FAILED
                    task.error = str(e)
                    self.stats['failed_tasks'] += 1
                    results.append({
                        'file': str(task.file_path),
                        'error': str(e),
                        'status': 'failed'
                    })
                
                self._notify_progress(task)
        
        # 統計を更新
        self._update_statistics()
        
        return results
    
    async def process_files_async(
        self,
        file_paths: List[Path],
        ocr_function: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        複数ファイルを非同期並列処理
        
        Args:
            file_paths: 処理するファイルパスのリスト
            ocr_function: OCR処理関数（省略時はデフォルト使用）
            
        Returns:
            処理結果のリスト
        """
        if not file_paths:
            return []
        
        # OCR関数の設定
        if ocr_function is None:
            ocr_function = self._default_ocr_function
        
        # タスクを作成
        tasks = []
        for i, file_path in enumerate(file_paths):
            task = OCRTask(
                file_path=file_path,
                task_id=f"async_task_{i}_{file_path.name}"
            )
            self.tasks[task.task_id] = task
            tasks.append(task)
        
        self.stats['total_tasks'] = len(tasks)
        
        # 非同期タスクを作成
        async_tasks = [
            self._process_single_file_async(task, ocr_function)
            for task in tasks
        ]
        
        # 並列実行
        results = await asyncio.gather(*async_tasks, return_exceptions=True)
        
        # 結果を処理
        processed_results = []
        for task, result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.error(f"Task {task.task_id} failed: {result}")
                task.status = ProcessingStatus.FAILED
                task.error = str(result)
                self.stats['failed_tasks'] += 1
                processed_results.append({
                    'file': str(task.file_path),
                    'error': str(result),
                    'status': 'failed'
                })
            else:
                processed_results.append(result)
            
            self._notify_progress(task)
        
        # 統計を更新
        self._update_statistics()
        
        return processed_results
    
    def _process_single_file(
        self,
        task: OCRTask,
        ocr_function: Callable
    ) -> Dict[str, Any]:
        """
        単一ファイルを処理
        
        Args:
            task: OCRタスク
            ocr_function: OCR処理関数
            
        Returns:
            処理結果
        """
        logger.info(f"Processing {task.file_path.name}...")
        
        task.status = ProcessingStatus.PROCESSING
        task.start_time = time.time()
        self._notify_progress(task)
        
        try:
            # OCR処理を実行
            result = ocr_function(task.file_path)
            
            # テキスト処理エンジンで分析
            if 'text' in result:
                processed = self.text_engine.process_text(
                    result['text'],
                    filename=task.file_path.name
                )
                result['analysis'] = self.text_engine.export_to_dict(processed)
            
            task.status = ProcessingStatus.COMPLETED
            task.result = result
            self.stats['completed_tasks'] += 1
            
            logger.info(f"Completed {task.file_path.name}")
            
        except Exception as e:
            logger.error(f"Error processing {task.file_path.name}: {e}")
            task.status = ProcessingStatus.FAILED
            task.error = str(e)
            raise
        
        finally:
            task.end_time = time.time()
            if task.duration:
                self.stats['total_duration'] += task.duration
        
        return result
    
    async def _process_single_file_async(
        self,
        task: OCRTask,
        ocr_function: Callable
    ) -> Dict[str, Any]:
        """
        単一ファイルを非同期処理
        
        Args:
            task: OCRタスク
            ocr_function: OCR処理関数
            
        Returns:
            処理結果
        """
        loop = asyncio.get_event_loop()
        
        # ブロッキング処理を別スレッドで実行
        return await loop.run_in_executor(
            None,
            self._process_single_file,
            task,
            ocr_function
        )
    
    def _default_ocr_function(self, file_path: Path) -> Dict[str, Any]:
        """
        デフォルトのOCR処理関数
        
        Args:
            file_path: ファイルパス
            
        Returns:
            OCR結果
        """
        # ここでは実際のOCR処理の代わりにダミーデータを返す
        # 実際の実装では、Google Cloud Vision APIなどを呼び出す
        
        logger.info(f"Default OCR processing for {file_path}")
        
        # PDFファイルの場合
        if file_path.suffix.lower() == '.pdf':
            # PDF処理のモック
            return {
                'text': f"Sample text from {file_path.name}",
                'pages': 1,
                'confidence': 0.95,
                'file': str(file_path)
            }
        
        # テキストファイルの場合
        elif file_path.suffix.lower() in ['.txt', '.text']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                return {
                    'text': text,
                    'file': str(file_path)
                }
            except Exception as e:
                raise Exception(f"Failed to read text file: {e}")
        
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
    
    def _update_statistics(self):
        """統計情報を更新"""
        if self.stats['completed_tasks'] > 0:
            self.stats['average_duration'] = (
                self.stats['total_duration'] / self.stats['completed_tasks']
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        return {
            **self.stats,
            'success_rate': (
                self.stats['completed_tasks'] / self.stats['total_tasks'] * 100
                if self.stats['total_tasks'] > 0 else 0
            ),
            'tasks': {
                task_id: {
                    'status': task.status.value,
                    'duration': task.duration,
                    'file': task.file_path.name
                }
                for task_id, task in self.tasks.items()
            }
        }
    
    def cancel_all_tasks(self):
        """全タスクをキャンセル"""
        for task in self.tasks.values():
            if task.status in [ProcessingStatus.PENDING, ProcessingStatus.PROCESSING]:
                task.status = ProcessingStatus.CANCELLED
                self._notify_progress(task)


class BatchOCRProcessor:
    """バッチOCR処理クラス"""
    
    def __init__(self, batch_size: Optional[int] = None):
        """
        初期化
        
        Args:
            batch_size: バッチサイズ（省略時は設定から取得）
        """
        self.config = get_config()
        self.batch_size = batch_size or self.config.processing.batch_size
        self.processor = ParallelOCRProcessor()
    
    def process_directory(
        self,
        directory: Path,
        pattern: str = "*.pdf",
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        ディレクトリ内のファイルをバッチ処理
        
        Args:
            directory: 処理対象ディレクトリ
            pattern: ファイルパターン
            recursive: 再帰的に検索するか
            
        Returns:
            処理結果のリスト
        """
        # ファイルを収集
        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))
        
        if not files:
            logger.warning(f"No files found matching {pattern} in {directory}")
            return []
        
        logger.info(f"Found {len(files)} files to process")
        
        # バッチに分割
        all_results = []
        for i in range(0, len(files), self.batch_size):
            batch = files[i:i + self.batch_size]
            logger.info(f"Processing batch {i // self.batch_size + 1} ({len(batch)} files)")
            
            # バッチを処理
            results = self.processor.process_files_parallel(batch)
            all_results.extend(results)
            
            # 進捗を表示
            completed = min(i + self.batch_size, len(files))
            progress = completed / len(files) * 100
            logger.info(f"Progress: {completed}/{len(files)} ({progress:.1f}%)")
        
        # 統計を表示
        stats = self.processor.get_statistics()
        logger.info(f"Processing complete: {stats['completed_tasks']} succeeded, {stats['failed_tasks']} failed")
        logger.info(f"Average processing time: {stats['average_duration']:.2f} seconds")
        
        return all_results


# 使用例
def example_usage():
    """使用例"""
    import asyncio
    
    # 同期版の使用例
    processor = ParallelOCRProcessor(max_workers=4)
    
    # 進捗コールバックを追加
    def progress_callback(task: OCRTask):
        print(f"Task {task.task_id}: {task.status.value}")
    
    processor.add_progress_callback(progress_callback)
    
    # ファイルリストを処理
    files = [
        Path("sample1.pdf"),
        Path("sample2.pdf"),
        Path("sample3.pdf")
    ]
    
    results = processor.process_files_parallel(files)
    
    # 統計を表示
    stats = processor.get_statistics()
    print(f"Success rate: {stats['success_rate']:.1f}%")
    print(f"Average time: {stats['average_duration']:.2f} seconds")
    
    # 非同期版の使用例
    async def async_example():
        processor = ParallelOCRProcessor(max_workers=4)
        results = await processor.process_files_async(files)
        return results
    
    # asyncio.run(async_example())
    
    # バッチ処理の使用例
    batch_processor = BatchOCRProcessor(batch_size=10)
    results = batch_processor.process_directory(
        Path("/path/to/pdfs"),
        pattern="*.pdf",
        recursive=True
    )


if __name__ == "__main__":
    # テスト実行
    example_usage()