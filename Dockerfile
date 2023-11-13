FROM ubuntu:22.04
RUN apt-get update && apt-get install python3-pip pandoc curl -y
RUN pip install requests click # TODO: pin version
RUN apt-get install texlive-latex-base texlive-latex-recommended texlive-fonts-recommended -y # TODO: move up
COPY main.py /main.py
CMD ["python3", "/main.py"]
