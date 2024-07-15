
# Travel Planner

## Description

The Travel Planner application helps users plan their trips by generating detailed itineraries based on their travel details. The backend utilizes LangGraph and Tavily API to fetch relevant travel information and generate comprehensive travel plans. The frontend is built using Streamlit, providing an easy-to-use interface for users to input their travel details.

## Features

- Generates detailed travel itineraries with daily schedules,and packing suggestions.
- Provides information on local attractions and hotels based on user preferences.
- Saves the generated itinerary as a Markdown file.

## Prerequisites

- Python 3.8 or higher
- [Streamlit](https://docs.streamlit.io/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [Tavily API](https://app.tavily.com/sign-in) (API Key required)

## Setup

1. **Clone the repository:**

    ```sh
    git clone https://github.com/siddartha-10/TAVILY_AGENTS.git
    cd TAVILY_AGENTS
    ```

2. **Install the required packages:**

    ```sh
    pip install -r requirements.txt
    ```

3. **Create a `.env` file in the root directory and add your API keys:**

    ```sh
    AZURE_OPENAI_KEY=your_azure_openai_key
    AZURE_OPENAI_VERSION=2023-07-01-preview
    AZURE_OPENAI_DEPLOYMENT=gpt4chat
    AZURE_OPENAI_ENDPOINT=https://gpt-4-trails.openai.azure.com/
    TAVILY_API_KEY=your_tavily_api_key
    ```

## Usage

1. **Run the Streamlit application:**

    ```sh
    streamlit run main.py
    ```

2. **Fill in the travel details in the sidebar:**

    - Where are you traveling from?
    - Where are you traveling to?
    - Hotel Preferences
    - Departure Date
    - Return Date

3. **Submit the form and wait for the itinerary to be generated.**

4. **The generated itinerary will be displayed on the main page and saved as a Markdown file named `{city_name}_itinerary.md` in the root directory.**

## Contribution

Contributions are welcome! If you have any ideas or improvements, feel free to submit a pull request. Please ensure that your changes are well-documented and covered by tests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenAI](https://openai.com/) for the language models.
- [Tavily](https://www.tavily.com/) for the data.
- [Streamlit](https://streamlit.io/) for the easy-to-use interface.
