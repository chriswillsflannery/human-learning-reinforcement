import { useEffect, useState } from 'react'
import axios from 'axios';
import './App.css'

function App() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [userAnswer, setUserAnswer] = useState('');
  const [evaluation, setEvaluation] = useState('');

  useEffect(() => {
    fetchQuestion();
  }, [])

  const fetchQuestion = async () => {
    try {
      const res = await axios.get('http://localhost:5000/api/question');
      setQuestion(res.data.question);
      setAnswer(res.data.answer);
      setUserAnswer('');
      setEvaluation('');
    } catch (error) {
      console.error('Error fetching question: ', error);
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post('http://localhost:5000/api/check_answer', {
        question,
        user_answer: userAnswer,
        correct_answer: answer,
      });
      setEvaluation(res.data.evaluation);
    } catch (error) {
      console.error('Error checking answer:', error);
    }
  }

  return (
    <div className="App">
      <h1>Trivia Game</h1>
      <div>
        <h2>Question:</h2>
        <p>{question}</p>
      </div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={userAnswer}
          onChange={(e) => setUserAnswer(e.target.value)}
          placeholder='Your answer'
        />
        <button type="submit">Submit</button>
      </form>
      {evaluation && (
        <div>
          <h2>Evaluation:</h2>
          <p>{evaluation}</p>
        </div>
      )}
      <button onClick={fetchQuestion}>Next Question</button>
    </div>
  )
}

export default App
