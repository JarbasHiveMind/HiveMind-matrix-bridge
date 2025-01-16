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
    install_requires=["hivemind_bus_client",
                      "python-matrixbot"],
    entry_points={
        'console_scripts': [
            'HiveMind-matrix=hm_matrix_bridge.__main__:main'
        ]
    }
)
