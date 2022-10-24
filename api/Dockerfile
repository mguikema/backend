# FROM registry.access.redhat.com/ubi8/python-39
FROM mguikema/ubi8-python-39-postgis

# ENV SUMMARY="Ubi8 base image with Proj, GDAL and GEOS preinstalled with cmake from OSGeo"

# LABEL summary="$SUMMARY" 

# USER root

# ENV CMAKE_VERSION=3.17.3 \
#     PROJ_VERSION=9.1.0 \
#     GDAL_VERSION=3.5.2 \
#     GEOS_VERSION=3.11.0 \
#     INSTALL_DIR=/cmake_tmp

# RUN mkdir -p ${INSTALL_DIR} && \
#     wget -P ${INSTALL_DIR}/ https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/cmake-${CMAKE_VERSION}.tar.gz \
#     https://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz \
#     https://download.osgeo.org/gdal/CURRENT/gdal-${GDAL_VERSION}.tar.gz \
#     https://download.osgeo.org/geos/geos-${GEOS_VERSION}.tar.bz2 && \
#     tar -zxvf ${INSTALL_DIR}/cmake-${CMAKE_VERSION}.tar.gz -C ${INSTALL_DIR}/ && \
#     tar -zxvf ${INSTALL_DIR}/proj-${PROJ_VERSION}.tar.gz -C ${INSTALL_DIR}/ && \
#     tar -zxvf ${INSTALL_DIR}/gdal-${GDAL_VERSION}.tar.gz -C ${INSTALL_DIR}/ && \
#     tar xvfj ${INSTALL_DIR}/geos-${GEOS_VERSION}.tar.bz2 -C ${INSTALL_DIR}/ && \
#     ${INSTALL_DIR}/cmake-${CMAKE_VERSION}/bootstrap && \
#     make -I ${INSTALL_DIR}/cmake-${CMAKE_VERSION} && \
#     make install -d ${INSTALL_DIR}/cmake-${CMAKE_VERSION} && \
#     mkdir ${INSTALL_DIR}/proj-${PROJ_VERSION}/build && \
#     cmake ${INSTALL_DIR}/proj-${PROJ_VERSION}/ -B ${INSTALL_DIR}/proj-${PROJ_VERSION}/build/ && \
#     cmake --build ${INSTALL_DIR}/proj-${PROJ_VERSION}/build/ && \
#     cmake --build ${INSTALL_DIR}/proj-${PROJ_VERSION}/build/ --target install && \
#     mkdir ${INSTALL_DIR}/gdal-${GDAL_VERSION}/build && \
#     cmake ${INSTALL_DIR}/gdal-${GDAL_VERSION}/ -B ${INSTALL_DIR}/gdal-${GDAL_VERSION}/build/ && \
#     cmake --build ${INSTALL_DIR}/gdal-${GDAL_VERSION}/build/ && \
#     cmake --build ${INSTALL_DIR}/gdal-${GDAL_VERSION}/build/ --target install && \
#     mkdir ${INSTALL_DIR}/geos-${GEOS_VERSION}/build && \
#     cmake ${INSTALL_DIR}/geos-${GEOS_VERSION}/ -B ${INSTALL_DIR}/geos-${GEOS_VERSION}/build/ && \
#     cmake --build ${INSTALL_DIR}/geos-${GEOS_VERSION}/build/ && \
#     cmake --build ${INSTALL_DIR}/geos-${GEOS_VERSION}/build/ --target install && \
#     ldconfig && \
#     rm -rf ${INSTALL_DIR}/ 

# ENV GDAL_LIBRARY_PATH=/usr/local/lib64/libgdal.so

ENV PYTHONUNBUFFERED 1

EXPOSE 8000

COPY requirements.txt /requirements.txt

RUN yum update \
    && yum install -y \
                nc \
                pkg-config \
                graphviz \
    && pip install -r /requirements.txt \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/

RUN chgrp root /app && chown root:2000 /app && chmod g+w /app
ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH

ENV DJANGO_SETTINGS_MODULE=signals.settings
ARG DJANGO_SECRET_KEY=insecure_docker_build_key

COPY app /app/
COPY deploy /deploy/

RUN mkdir -p /media && mkdir -p /static && chown 2000 /media && chown 2000 /static

USER 2000

RUN SECRET_KEY=$DJANGO_SECRET_KEY python manage.py collectstatic --no-input
# CMD uwsgi \ 
#     --master \
#     --http=0.0.0.0:8000
#     --callable=application \
#     --module=signals.wsgi:application \
#     --static-index=index.html \
#     --static-map=/signals/static=/static \
#     --static-map=/signals/media=/media \
#     --buffer-size=8192 \
#     --harakiri=15 \
#     --py-auto-reload=1 \
#     --die-on-term