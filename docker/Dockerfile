FROM continuumio/miniconda3:4.10.3

# Update, upgrade, and install osmium-tool
RUN apt update -qq && apt upgrade -y \
 && apt install -y osmium-tool --no-install-recommends \
 && apt clean -y \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY environment.yml /workspace/environment.yml

RUN conda install -y mamba -n base -c conda-forge

RUN mamba env update --file /workspace/environment.yml

COPY osmconf.ini /opt/conda/share/gdal/osmconf.ini
COPY jupyter_notebook_config.py /root/.jupyter/jupyter_lab_config.py

EXPOSE 8888

CMD [ "jupyter-lab" ]
