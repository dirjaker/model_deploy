"""
py2app setup script for Model Deploy macOS application.
Build with: python packaging/py2app_setup.py py2app
"""
from setuptools import setup

APP = ['src/macos/app.py']
DATA_FILES = [
    ('src/web/static', ['src/web/static/index.html']),
]
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'CFBundleName': 'Model Deploy',
        'CFBundleDisplayName': 'Model Deploy',
        'CFBundleIdentifier': 'com.modeldeploy.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'MIT License',
    },
    'packages': [
        'fastapi', 'uvicorn', 'pydantic', 'starlette', 'anyio',
        'h11', 'httpcore', 'httptools', 'yaml',
    ],
    'includes': [
        'tkinter', 'json', 'threading', 'webbrowser',
        'src.web.app', 'models', 'model_manager', 'inference_engine', 'quantizer',
    ],
    'excludes': ['numpy', 'torch', 'transformers'],
}

setup(
    name='Model Deploy',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
