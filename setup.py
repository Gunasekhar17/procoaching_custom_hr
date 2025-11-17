from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="procoaching_custom_hr",
    version="0.0.1",
    description="Custom HR modifications for Pro Coaching",
    author="Pro Coaching",
    author_email="info@pro-coaching.co.uk",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)
