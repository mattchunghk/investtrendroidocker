FROM amazonlinux:2

# Enable Python 3.8 from Amazon Linux Extras and install it
RUN amazon-linux-extras enable python3.8 && \
    yum clean metadata && \
    yum -y install python3.8 && \
    python3.8 -m ensurepip && \
    python3.8 -m pip install --upgrade pip && \
    python3.8 -m pip install virtualenv

# Create a virtual environment and activate it
RUN python3.8 -m virtualenv /lambda-env

# Set the virtual environment as the default python environment
ENV VIRTUAL_ENV=/lambda-env
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN chmod +x /lambda-env/bin/python

# Copy the requirements.txt file into the image
COPY requirements.txt .

# Install the Python dependencies in requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY src/ .

# Command to run on container start
# Make sure to specify the full path to the python executable from the virtual environment
CMD [ "/lambda-env/bin/python", "./server.py" ]