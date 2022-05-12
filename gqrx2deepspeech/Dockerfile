FROM python:3.7.6

COPY . /src
RUN chmod -R 777 /src
ENV WORKDIR /src

RUN apt-get update
RUN apt-get install libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev -y

RUN pip install -r /src/requirements.txt

ENTRYPOINT [ "/src/run.sh" ]
