FROM python:3.6-slim

MAINTAINER Laurent Vaylet <laurent.vaylet@gmail.com>

WORKDIR "/usr/src/app"

# Install packages
# Leverage Docker's caching by only copying `requirements.txt`
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bundle the app's source code into the container
COPY . .

# Expose Gunicorn
EXPOSE 8000

# Set PYTHONPATH so modules are found and loaded correctly
ENV PYTHONPATH .
