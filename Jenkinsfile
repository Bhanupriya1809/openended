pipeline {
    agent any
    
    environment {
        IMAGE_NAME = "bhanupriya18/smart_health_reminder"
        CONTAINER_NAME = "smart_health_app"
    }

    stages {

        stage('Clone Repository') {
            steps {
                git branch: 'master',
                    url: 'https://github.com/Bhanupriya1809/openended.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${IMAGE_NAME}:latest")
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'dockerhub-credentials') {
                        docker.image("${IMAGE_NAME}:latest").push()
                    }
                }
            }
        }

        stage('Deploy Container') {
            steps {
                script {
                    // Stop old running container
                    sh "docker stop ${CONTAINER_NAME} || true"
                    sh "docker rm ${CONTAINER_NAME} || true"

                    // Deploy the new image
                    sh """
                        docker run -d --name ${CONTAINER_NAME} \
                        -p 5000:5000 ${IMAGE_NAME}:latest
                    """
                }
            }
        }
    }
}
