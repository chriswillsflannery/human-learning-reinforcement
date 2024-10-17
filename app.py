from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import json
from botocore.exceptions import ClientError
import os

app = Flask(__name__)
CORS(app)

def set_aws_credentials_from_secrets():
    secret_name = "human-learning-reinforcement-access-key"
    region_name = "us-east-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        secret = json.loads(get_secret_value_response['SecretString'])
        
        os.environ['AWS_ACCESS_KEY_ID'] = secret['AWS_ACCESS_KEY_ID']
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret['AWS_SECRET_ACCESS_KEY']
    except ClientError as e:
        print(f"Error retrieving secrets: {e}")
        raise

set_aws_credentials_from_secrets()

# if we don't explicitly pass API keys to clinet invocation boto3
# will use credential provider chain to look in env vars
bedrock = boto3.client(
    service_name='bedrock_runtime',
    region_name='us-east-1'
)

def invoke_bedrock_model(prompt, max_tokens=100):
    body = json.dumps({
        "prompt":prompt,
        "max_tokens_to_sample":max_tokens,
        "temperatur":0.5,
        "top_p":0.9,
    })

    response = bedrock.invoke_model(
        body=body,
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
        accept="application/json",
        contentType="application/json"
    )

    response_body = json.loads(response.get('body').read())
    return response_body.get('completion')

@app.route('/api/question', methods=['GET'])
def get_question():
    prompt = "Generate a trivia question with its answer. Format: Question [question] Answer: [answer]"
    response = invoke_bedrock_model(prompt)

    lines = response.strip().split('\n')
    question = lines[0].replace('Question: ', '')
    answer = lines[1].replace('Answer: ', '')

    return jsonify({"question": question, "answer": answer})

@app.route('/api/check_answer', methods=['POST'])
def check_answer():
    data = request.json
    question = data.get('question')
    user_answer = data.get('user_answer')
    correct_answer = data.get('correct_answer')

    prompt = f"Question: {question}\nCorrect Answer: {correct_answer}\nUser Answer: {user_answer}\nEvaluate the user's answer and provide a score out of 10:"
    evaluation = invoke_bedrock_model(prompt)

    return jsonify({"evaluation": evaluation})

if __name__ == '__main__':
    app.run(debug=True)
