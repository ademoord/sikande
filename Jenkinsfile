pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                git branch: 'dev2', url: 'https://github.com/andromedasupendi/sikande.git'
            }
        }
        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        stage('Test') {
            steps {
                sh 'python -m pytest tests'
            }
        }
        stage('Lint') {
            steps {
                sh 'flake8'
            }
        }
        stage('Build and Deploy') {
            environment {
                FLASK_APP = 'sikande/flask_app.py'
                FLASK_ENV = 'production'
            }
            steps {
                sh 'flask db upgrade'
                sh 'flask run'
            }
        }
    }
}

