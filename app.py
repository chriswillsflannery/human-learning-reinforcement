from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import boto3
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

bedrock = boto3.client(
    service_name='bedrock_runtime',
    region_name='us-east-1',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
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