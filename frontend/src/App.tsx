import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          BIBBI Sales Analytics Platform
        </h1>
        <p className="text-lg text-gray-600 mb-8">
          Multi-channel sales data analytics with AI-powered insights
        </p>
        <div className="flex gap-4 justify-center">
          <button
            onClick={() => setCount((count) => count + 1)}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Count: {count}
          </button>
        </div>
        <p className="mt-8 text-sm text-gray-500">
          Frontend: React 19 + Vite 6 + TypeScript | Backend: FastAPI + Supabase
        </p>
      </div>
    </div>
  )
}

export default App
