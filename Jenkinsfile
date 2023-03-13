pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                git branch: 'dev3', url: 'https://github.com/andromedasupendi/sikande.git'
            }
        }
        stage('SonarQube analysis') {
            steps {
                withSonarQubeEnv('sonarqube') {
                    sh 'sonar-scanner'
                }
            }
        }
        stage('Lint') {
            steps {
                sh 'git checkout dev3'
                sh 'flake8'
            }
        }
        stage('Build and Deploy') {
            environment {
                FLASK_APP = 'sikande/flask_app.py'
                FLASK_ENV = 'production'
            }
            steps {
                sh 'git checkout dev3'
                sh 'flask db upgrade'
                sh 'flask run'
            }
        }
    }
}

