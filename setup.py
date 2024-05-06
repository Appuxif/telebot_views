import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='telebot_views',
    version='0.0.19b4',
    author='Appuxif',
    author_email='app@mail.com',
    description='A Python package with views for building telebot apps',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Appuxif/telebot_views',
    project_urls={
        'Bug Tracker': 'https://github.com/Appuxif/telebot_views/issues',
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    package_dir={'': '.'},
    packages=[
        'telebot_views',
        'telebot_views.models',
        'telebot_views.views',
        'telebot_views.services',
        'telebot_views.decorators',
    ],
    package_data={},
    python_requires='>=3.8',
    install_requires=[
        "pytelegrambotapi>=4.10.0,<5.0.0",
        "telebot_models>=0.0.2,<1.0.0",
        "pydantic>=1.10.9,<1.20.0",
        "asyncio_functools>=0.0.1,<1.0.0",
    ],
)
