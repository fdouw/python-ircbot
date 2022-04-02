
FROM ubuntu:latest

# Install requirements
RUN apt update \
    && apt install -y --no-install-recommends python3 python3-pip \
    && python3 -m pip install requests toml

# Config for better prompt
RUN echo 'PS1="\[\e]\u@\h: \w\a\]${debian_chroot:+($debian_chroot)}\[\033[02;36m\]\u@\h\[\033[00m\]:\[\033[01;36m\]\w\[\033[00m\]\$ "' >> /root/.bashrc

# Add folder with the python and config files for the bot, and make it our start folder
ADD bot /mnt/mkbotje
WORKDIR /mnt/mkbotje

# Start the bot when running the container
ENTRYPOINT [ "python3", "botje.py" ]