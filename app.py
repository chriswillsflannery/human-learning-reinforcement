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
client = boto3.client("bedrock-runtime", region_name="us-east-1")

def invoke_bedrock_model(prompt, max_tokens=100):
    model_id="anthropic.claude-3-haiku-20240307-v1:0"

    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }

    # convert native request to json
    request = json.dumps(native_request)

    try:
        response = client.invoke_model(modelId=model_id, body=request)
    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)

    model_response = json.loads(response['body'].read())
    response_text = model_response['content'][0]['text']
    return response_text

@app.route('/api/question', methods=['GET'])
def get_question():
    prompt = (
        "Generate an open-ended trivia question with its answer.\n"
        "Format: Question [question] Answer: [answer]\n"
        "The correct answer should NEVER be a single word.\n"
        "There should ALWAYS be a single correct answer which is about 2 or 3 sentences long."
    )
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

    prompt = (
        f"Question: {question}\n"
        f"Correct Answer: {correct_answer}\n"
        f"User Answer: {user_answer}\n"
        "Evaluate the user's answer and provide a score out of 10."
        "The user's answer doesn't have to be the exact same string of words as the correct answer to be considered correct."
        "To be considered correct, the user's answer should be as semantically similar as the correct answer, and contain the correct hard facts such as names and numerical values."
    )
    evaluation = invoke_bedrock_model(prompt)

    return jsonify({"evaluation": evaluation})

if __name__ == '__main__':
    app.run(debug=True)
