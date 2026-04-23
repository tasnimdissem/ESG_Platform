
  # ESG Prediction Platform

  This is a code bundle for ESG Prediction Platform. The original project is available at https://www.figma.com/design/8mLtfTH9W7kWxCcBaJuwg9/ESG-Prediction-Platform.

  ## Running the code

  Run `npm i` to install the dependencies.

  Run `npm run dev` to start the development server.

    ## RAG Integration Setup

    The chatbot endpoint (`/api/v1/integration`) can call an external RAG service.

    1. Install backend dependencies:
      - `pip install -r backend/requirements.txt`
    2. Create a local env file:
      - Copy `.env.example` to `.env`
    3. Set your remote RAG endpoint and token in `.env`:
      - `RAG_API_URL` or `RAG_API_BASE_URL` + `RAG_INTEGRATION_PATH`
      - `RAG_API_TOKEN` if required
    4. Choose behavior on remote failure:
      - `RAG_ALLOW_LOCAL_FALLBACK=true` to silently use local fallback
      - `RAG_ALLOW_LOCAL_FALLBACK=false` to return HTTP 502 with clear error
    5. Start full stack:
      - `npm run dev:full`
  