from setuptools import setup
import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))

with open(f"{BASEDIR}/README.md", "r") as fh:
    long_desc = fh.read()


def get_version():
    """ Find the version of the package"""
    version_file = os.path.join(BASEDIR, 'hm_matrix_bridge', 'version.py')
    major, minor, build, alpha = (None, None, None, None)
    with open(version_file) as f:
        for line in f:
            if 'VERSION_MAJOR' in line:
                major = line.split('=')[1].strip()
            elif 'VERSION_MINOR' in line:
                minor = line.split('=')[1].strip()
            elif 'VERSION_BUILD' in line:
                build = line.split('=')[1].strip()
            elif 'VERSION_ALPHA' in line:
                alpha = line.split('=')[1].strip()

            if ((major and minor and build and alpha) or
                    '# END_VERSION_BLOCK' in line):
                break
    version = f"{major}.{minor}.{build}"
    if int(alpha):
        version += f"a{alpha}"
    return version


def required(requirements_file):
    """ Read requirements file and remove comments and empty lines. """
    with open(os.path.join(BASEDIR, requirements_file), 'r') as f:
        requirements = f.read().splitlines()
        if 'MYCROFT_LOOSE_REQUIREMENTS' in os.environ:
            print('USING LOOSE REQUIREMENTS!')
            requirements = [r.replace('==', '>=').replace('~=', '>=') for r in requirements]
        return [pkg for pkg in requirements
                if pkg.strip() and not pkg.startswith("#")]


setup(
    name='HiveMind-matrix-bridge',
    version=get_version(),
    packages=['hm_matrix_bridge'],
    url='https://github.com/JarbasHiveMind/HiveMind-matrix-bridge',
    license='MIT',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='matrix bridge for hivemind',
    long_description=long_desc,
    long_description_content_type='text/markdown',
    install_requires=required("requirements.txt"),
    entry_points={
        'console_scripts': [
            'HiveMind-matrix=hm_matrix_bridge.__main__:main'
        ]
    }
)
