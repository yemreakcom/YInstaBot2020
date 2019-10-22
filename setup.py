from distutils.core import setup
import setuptools


version = ""
with open(".version", "r", encoding="utf-8") as file:
    version = (int(file.read().strip()) + 1) / 10

long_description = ""
with open("README.md", "r", encoding="utf-8") as file:
    long_description = file.read()


setup(
    name='yinstabot',         # How you named your package folder (MyLib)
    packages=setuptools.find_packages(),   # Chose the same as "name"
    # Start with a small number and increase it with every change you make
    version=version,
    # Chose a license from here: https://help.github.com/articles/licensing-a-repository
    license='MIT',
    # Give a short description about your library
    description='Instagram bot',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Yunus Emre Ak',                   # Type in your name
    author_email='yedhrab@gmail.com',      # Type in your E-Mail
    # Provide either the link to your github or to your website
    url='https://github.com/yedhrab/YInstabot',
    # I explain this later on
    download_url=f'https://github.com/yedhrab/YPackage/archive/{version}.tar.gz',
    # Keywords that define your package best
    keywords=['instabot', 'yinstabot', 'instagrambot', 'neoinstabot', 'instabot-py'],
    install_requires=['ypackage', 'certifi', 'chardet', 'huepy', 'idna', 'lazy',
                      'post', 'public', 'pytz', 'query', 'requests', 'six', 'tqdm', 'urllib3', 'wrapt'],
    classifiers=[
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Development Status :: 3 - Alpha',
        # Define that your audience are developers
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',   # Again, pick a license
        # Specify which pyhton versions that you want to support
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    # WARN: Dosya değişikliğinde burası düzenlenmeli
    entry_points={
        'console_scripts': [
            'yinstabot = yinstabot.workspace:main',
        ]
    },
)

with open(".version", "w", encoding="utf-8") as file:
    file.write(str(int(version * 10)))
