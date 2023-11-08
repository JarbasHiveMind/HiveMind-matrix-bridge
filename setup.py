from setuptools import setup

setup(
    name='HiveMind-matrix-bridge',
    version='0.0.2',
    packages=['hm_matrix_bridge'],
    url='https://github.com/JarbasHiveMind/HiveMind-matrix-bridge',
    license='MIT',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='',
    install_requires=["jarbas_hive_mind>=0.10.7",
                      "python-matrixbot"],
    entry_points={
        'console_scripts': [
            'HiveMind-matrix=matrix_bridge.__main__:main'
        ]
    }
)
