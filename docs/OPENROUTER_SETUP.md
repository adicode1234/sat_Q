# OpenRouter setup

Double-click `Start OpenRouter.command` in the SatQuery project folder, or run:

```sh
cd /Users/adityarajput/Downloads/satquery-ai
./Start\ OpenRouter.command
```

Open http://127.0.0.1:8766/vision-setup, select **OpenRouter**, paste your key into **API Key**, and click **Connect and enable vision AI**. Leave Model Name blank for `google/gemini-2.5-flash`, or enter another OpenRouter model ID supporting image inputs. Setup checks the key and current model catalog without paid inference or image upload. An authenticated key does not guarantee credits or inference availability.

Return to http://127.0.0.1:8766 and upload images. Explicitly connecting OpenRouter automatically selects the cloud analysis path; legacy mode is not required. Results disclose OpenRouter and the returned model name. Disabling the connection returns to the configured local pipeline. An unavailable API fails explicitly without local model substitution.

Keys are held in server memory, not source code, reports, browser local storage or a project file. Enter the key again after restarting the server. Never put it in frontend code. For server deployments, the alternative environment variables are `SATQUERY_VISION_PROVIDER=openrouter`, `SATQUERY_CLOUD_VISION=1`, `OPENROUTER_API_KEY`, and optional `OPENROUTER_MODEL`. Environment-provided credentials bypass the setup-page catalog check; select a compatible model yourself. Setup automatically selects native JSON schema, JSON-object mode or JSON prompting based on catalog capabilities. All modes retain local report validation; invalid answers fail explicitly.

Uploads and questions go to OpenRouter and its selected model provider when analysis runs. Account credits/provider charges apply. Cloud analysis is not GeoChat, TEOChat or EarthMind inference; it is unverified visual interpretation. No fabricated spatial overlay, confidence percentage or hazard/absence findings are added. Temporal-reference and missing-sensor guards still apply before API calls.

Official references:
- https://openrouter.ai/docs/guides/overview/multimodal/image-understanding
- https://openrouter.ai/docs/guides/features/structured-outputs
- https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key

Validation uses mocked provider responses for requests/errors plus real local API/upload/export tests. A live authenticated OpenRouter inference requires the user's key and has not been run by the agent.

Verification on this change: 138 pytest tests passed; TypeScript no-emit, production build, Python compile checks and launcher shell syntax passed. Provider calls in tests were mocked; no live key was used.
