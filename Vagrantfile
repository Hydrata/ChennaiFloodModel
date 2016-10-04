# -*- mode: ruby -*-
# vi: set ft=ruby :
raise "vagrant-secret plugin must be installed. https://github.com/tcnksm/vagrant-secret" unless Vagrant.has_plugin? "vagrant-secret"
Vagrant.configure(2) do |config|
    config.vm.box = "ubuntu/trusty64"
    config.vm.provider "virtualbox" do |vb|
        vb.memory = "6096" #adjust this based on your dev laptop memory capacity
    end
    config.vm.provision "shell" do |local|
        local.inline = $LocalScript
        #pass these args to the provisioning script from secret.yaml (see https://github.com/tcnksm/vagrant-secret)
        local.args = [
                Secret.AWS_SECRET_ACCESS_KEY,
                Secret.AWS_ACCESS_KEY_ID,
                Secret.AWS_PRIVATE_KEY_NAME,
                Secret.AWS_PRIVATE_KEY_PATH,
                Secret.AWS_ELASTIC_IP,
                Secret.AWS_SECURITY_GROUP,
                Secret.SQA_ENGINE,
                Secret.SQA_USER,
                Secret.SQA_PASSWORD,
                Secret.SQA_HOST,
                Secret.SQA_PORT,
                Secret.SQA_DATABASE,
                Secret.GITHUB_PW,
                Secret.GITHUB_UN,
                Secret.RABBIT_BROKER
        ]
    end
    config.vm.synced_folder '.', '/vagrant/ChennaiFloodModel', disabled: false # disable default rsync to avoid confusion if searching the server.

    config.vm.provider :aws do |aws, override|
        override.vm.box = "dummy"
        override.vm.synced_folder '.', '/vagrant', disabled: true # usually don't want to rsync with aws
        aws.access_key_id = Secret.AWS_ACCESS_KEY_ID
        aws.secret_access_key = Secret.AWS_SECRET_ACCESS_KEY
        aws.keypair_name = Secret.AWS_PRIVATE_KEY_NAME
        aws.region = "ap-southeast-2"
        aws.ami = "ami-6c14310f" #ubuntu 14.04 LTS server
        aws.instance_type = "m3.medium"
        aws.security_groups = Secret.AWS_SECURITY_GROUP
        aws.elastic_ip = Secret.AWS_ELASTIC_IP
        override.ssh.username = "ubuntu"
        override.ssh.private_key_path = Secret.AWS_PRIVATE_KEY_PATH
        override.vm.provision "shell" do |ec2|
            ec2.inline = $AWSScript
            #this passes these environment variables to the provisioning script from your secret.yaml file
            #(see https://github.com/tcnksm/vagrant-secret)
            ec2.args = [
                Secret.AWS_SECRET_ACCESS_KEY,
                Secret.AWS_ACCESS_KEY_ID,
                Secret.AWS_PRIVATE_KEY_NAME,
                Secret.AWS_PRIVATE_KEY_PATH,
                Secret.AWS_ELASTIC_IP,
                Secret.AWS_SECURITY_GROUP,
                Secret.SQA_ENGINE,
                Secret.SQA_USER,
                Secret.SQA_PASSWORD,
                Secret.SQA_HOST,
                Secret.SQA_PORT,
                Secret.SQA_DATABASE,
                Secret.GITHUB_PW,
                Secret.GITHUB_UN,
                Secret.RABBIT_BROKER
            ]
        end
    end
end


# Main Provisioning Shell Script
$LocalScript = <<SCRIPT
    set -x # Print commands and their arguments as they are executed.
    exec > >(tee -i LocalScript.log)
    exec 2>&1
    echo starting LocalScript
    date

    echo export AWS_SECRET_ACCESS_KEY=$1 | sudo tee --append /etc/environment
    echo export AWS_ACCESS_KEY_ID=$2 | sudo tee --append /etc/environment
    echo export AWS_PRIVATE_KEY_NAME=$3 | sudo tee --append /etc/environment
    echo export AWS_PRIVATE_KEY_PATH=$4 | sudo tee --append /etc/environment
    echo export AWS_ELASTIC_IP=$5 | sudo tee --append /etc/environment
    echo export AWS_SECURITY_GROUP=$6 | sudo tee --append /etc/environment
    echo export SQA_ENGINE=$7 | sudo tee --append /etc/environment
    echo export SQA_USER=$8 | sudo tee --append /etc/environment
    echo export SQA_PASSWORD=$9 | sudo tee --append /etc/environment
    echo export SQA_HOST=${10} | sudo tee --append /etc/environment
    echo export SQA_PORT=${11} | sudo tee --append /etc/environment
    echo export SQA_DATABASE=${12} | sudo tee --append /etc/environment
    echo export GITHUB_PW=${13} | sudo tee --append /etc/environment
    echo export GITHUB_UN=${14} | sudo tee --append /etc/environment
    echo export RABBIT_BROKER=${15} | sudo tee --append /etc/environment

    echo export PROD_IP=${21} | sudo tee --append /etc/environment

    sudo apt-get update
    sudo apt-get install -y git
    git clone https://github.com/GeoscienceAustralia/anuga_core.git
    export ANUGA_PARALLEL="mpich2"
    cd anuga_core
    bash tools/install_ubuntu.sh
    sudo apt-get install -y python-psycopg2
    sudo pip install wget
    sudo pip install SQLAlchemy
    cd /home/vagrant
    git clone https://${14}:${13}@github.com/Hydrata/anuganode.git
    sudo chmod -R 777 /home/vagrant/anuganode
    sudo pip install Celery
    sudo pip install gitpython

    echo finishing LocalScript >&2
SCRIPT

$AWSScript = <<SCRIPT
    set -x
    exec > >(tee -i AWSScript.log)
    exec 2>&1
    date
    echo "starting AWSScript"
    sudo cp /home/vagrant/anuganode/config/celeryd /etc/default
    sudo cp /home/vagrant/anuganode/config/generic-init.d/celeryd /etc/init.d/
    sudo /etc/init.d/celeryd status
    sudo /etc/init.d/celeryd start
    date
    echo finished AWSScript >&2
SCRIPT

