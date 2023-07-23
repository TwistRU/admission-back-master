pipeline {
    agent any

    environment {
        PATH = "$PATH:/usr/local/bin"
    }

    stages {
        stage("Build master") {
            when {
                branch 'master'
            }
            environment {
                BACKEND_PORT = "8005"
                DATA_PATH = '/home/twistru/Документы/ДВФУ/ПК/DashbordForRector/admission-back-master/data'
                BACKEND_ENV_ID = 'env-dev' // env-prod || env-dev
            }
            steps {
                buildBackend(BACKEND_ENV_ID)
                deployBackend()
            }
        }
    }
}

def deployBackend() {
    echo "Stopping previous container..."
    sh "docker-compose down"
    echo "Deploying..."
    sh "docker-compose up -d"
    echo "Deployed!"
}

def buildBackend(envID) {
    withCredentials([
        file(credentialsId: envID, variable: 'ENV'),
    ]) {
        echo "Creating .env"
        sh "rm -f .env"
        sh "cp $ENV .env"
    }

    echo "Building..."
    sh "docker-compose build"
    echo "Built!"
}