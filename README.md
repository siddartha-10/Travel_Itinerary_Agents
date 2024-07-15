
# Travel Planner

## Description

The Travel Planner application helps users plan their trips by generating detailed itineraries based on their travel details. The backend utilizes LangGraph and Tavily API to fetch relevant travel information and generate travel plans. The frontend is built using Streamlit, providing an easy-to-use interface for users to input their travel details. The fun part is along the way you can also see the outputs of search
results.

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
    git clone https://github.com/siddartha-10/Travel_Itinerary_Agents.git
    cd Travel_Itinerary_Agents
    ```

2. **Install the required packages:**

    ```sh
    pip install -r requirements.txt
    ```

3. **Edit the `.env_example` file in the root directory and add your API keys:**

    ```sh
    AZURE_OPENAI_KEY=your_azure_openai_key
    AZURE_OPENAI_VERSION=2023-07-01-preview
    AZURE_OPENAI_DEPLOYMENT=your-deployment-name
    AZURE_OPENAI_ENDPOINT=your-end-point
    OPENAI_API_KEY=your-openai-api_key
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

## Futher Improvements to be made

1) Speed up.
2) Improve the UI/UX.
3) Add human in the loop to see the user is happy and based on that build a plan.
3) Include the Transportation details as well(ex:- [Notebook](examples/langgraph_solo.ipynb) something very close to the final output of the notebook give transport details).
4) Turn this into the ultimate travel planning app.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenAI](https://openai.com/) for the language models.
- [Tavily](https://www.tavily.com/) for the data.
- [Streamlit](https://streamlit.io/) for the easy-to-use interface.
