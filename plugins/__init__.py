# Plugins module initialization
from .base import SchoolAnalyzerPlugin, PluginInfo
from .musashi_plugin import MusashiPlugin
from .kaisei_plugin import KaiseiPlugin
from .ouin_plugin import OuinPlugin
from .default_plugin import DefaultPlugin

__all__ = [
    'SchoolAnalyzerPlugin',
    'PluginInfo',
    'MusashiPlugin',
    'KaiseiPlugin', 
    'OuinPlugin',
    'DefaultPlugin',
]