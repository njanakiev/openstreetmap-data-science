FROM continuumio/miniconda3:4.7.12

# Update, upgrade, and install osmium-tool
RUN apt update -qq && apt upgrade -y \
 && apt install -y osmium-tool --no-install-recommends \
 && apt clean -y \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY environment.yml /workspace/environment.yml

RUN conda env update --file /workspace/environment.yml

COPY osmconf.ini /opt/conda/share/gdal/osmconf.ini

EXPOSE 8888

CMD [ "jupyter-lab", \
    "--ip=0.0.0.0", \
    "--port=8888", \
    "--ContentsManager.allow_hidden=True", \
    "--ServerApp.password=sha1:f07a23d068be:e96ca16aa940c4683af6b920b7e1a7f0206f2961", \
    "--notebook-dir=/workspace", \
    "--no-browser", \
    "--allow-root" ]
