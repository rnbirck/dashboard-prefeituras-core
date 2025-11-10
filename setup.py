from setuptools import setup, find_packages

setup(
    name="dashboard_core",
    version="0.1.0",
    description="Código principal compartilhado para dashboards municipais.",
    author="Renan Birck",
    author_email="renanbirck@outlook.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "python-dotenv==1.0.1",
        "supabase==2.7.2",
        "streamlit==1.49.1",
        "pandas==2.3.2",
        "numpy==2.3.2",
        "plotly==6.3.0",
        "openpyxl==3.1.5",
        "pyarrow==21.0.0",
        "matplotlib",
    ],
)
