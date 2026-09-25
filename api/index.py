import json
import os
import time
from flask import Flask, render_template_string, request
from google import genai
from google.genai import errors

app = Flask(__name__)

# Initialize Gemini Client (automatically reads GEMINI_API_KEY env var)
client = genai.Client()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Feynman AI - Learn by Teaching</title>
    <!-- Tailwind CSS CDN -->
    <script src="[https://cdn.tailwindcss.com](https://cdn.tailwindcss.com)"></script>
    <link href="[https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap](https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap)" rel="stylesheet">
    <style>
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: #0f172a;
            color: #f8fafc;
        }
        .glass {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .glass-input {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .glass-input:focus {
            border-color: #6366f1;
            outline: none;
            box-shadow: 0 0 15px rgba(99, 102, 241, 0.3);
        }
    </style>
</head>
<body class="min-h-screen flex flex-col justify-between p-4 md:p-8">

    <!-- Header -->
    <header class="max-w-4xl mx-auto w-full flex justify-between items-center mb-8">
        <div class="flex items-center gap-3">
            <div class="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center font-bold text-xl shadow-lg shadow-indigo-500/30">
                ⚛️
            </div>
            <span class="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-slate-400">
                Feynman<span class="text-indigo-400">AI</span>
            </span>
        </div>
        <span class="text-xs px-3 py-1.5 rounded-full glass text-slate-400 border border-slate-700">
            Feynman Technique Engine
        </span>
    </header>

    <!-- Main Content -->
    <main class="max-w-4xl mx-auto w-full grid grid-cols-1 md:grid-cols-12 gap-8 mb-auto">
        
        <!-- Input Form (Left Side) -->
        <div class="md:col-span-6 flex flex-col gap-5">
            <div class="glass p-6 rounded-2xl shadow-xl">
                <h1 class="text-2xl font-bold mb-2">Teach to Learn</h1>
                <p class="text-slate-400 text-sm mb-6">
                    Pick a concept and explain it as if you were teaching a 12-year-old. The AI will find your gaps.
                </p>

                <form method="POST" class="flex flex-col gap-4">
                    <div>
                        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Topic Name</label>
                        <input type="text" name="topic" value="{{ topic }}" placeholder="e.g. Black Holes, Photosynthesis, Inflation" required
                               class="w-full glass-input rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 transition-all">
                    </div>

                    <div>
                        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Your Plain-English Explanation</label>
                        <textarea name="explanation" rows="6" placeholder="Explain the core mechanism without relying on buzzwords or jargon..." required
                                  class="w-full glass-input rounded-xl p-4 text-sm text-white placeholder-slate-500 transition-all resize-none">{{ explanation }}</textarea>
                    </div>

                    <button type="submit" class="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold shadow-lg shadow-indigo-500/25 transition-all duration-200 active:scale-[0.98]">
                        Analyze Explanation
                    </button>
                </form>
            </div>
        </div>

        <!-- Evaluation Panel (Right Side) -->
        <div class="md:col-span-6">
            {% if error_msg %}
            <div class="glass p-6 rounded-2xl shadow-xl border border-rose-500/30 bg-rose-500/10 mb-6">
                <h3 class="text-sm font-bold text-rose-400 mb-1">⚠️ Request Failed</h3>
                <p class="text-xs text-slate-300">{{ error_msg }}</p>
            </div>
            {% endif %}

            {% if result %}
            <div class="glass p-6 rounded-2xl shadow-xl flex flex-col gap-6">
                
                <!-- Score Bar -->
                <div class="flex items-center justify-between border-b border-slate-700/50 pb-4">
                    <div>
                        <h2 class="text-lg font-bold text-white">Clarity Score</h2>
                        <p class="text-xs text-slate-400">Based on simplicity & accuracy</p>
                    </div>
                    <div class="text-3xl font-extrabold text-indigo-400 bg-indigo-500/10 px-4
