from setuptools import setup, find_packages

setup(
    name='website-monitor',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A Python project for monitoring website changes and sending notifications.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/website-monitor',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'requests',
        'beautifulsoup4',
        'plyer',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)