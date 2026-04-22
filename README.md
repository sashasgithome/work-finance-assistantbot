# Finance Bot Prototype

### ABOUT

This project showcases the proof-of-concept for a chatbot integrated inside a banking app downloaded within a partiuclar user's phone. 

The chatbot is able to :
- answer questions regarding a customer's transaction history
- provide proper responses if given (1) queries unrelated to finance, and (2) queries outside chatbot's analysis capabilities in natural language.
  
The chatbot is designed with ***accuracy*** as priority, ensuring base LLM agent gives *answers that are grounded on the actual customer database* (handle hallucination).

<br>

### FEATURES & LIMITATIONS

The chatbot ensures good user experience and overall data security through the following features : 
- language used will automatically adjust to the user's preference (English/Indonesian),
- user is engaged in personal, first-name basis conversation,
- customer can only ever access their own data, rendering _prompt injection_ useless, and
- double-filtering is applied to give as minimal data to LLM as possible.

LLM never accesses the entire user data _at once_ and mathematical processes are performed manually in code.
As such, the chatbot's capabilities are limited to : (1) listing, (2) finding max/min, and (3) summation of transactions. 

| Type | Example Question | 
| --- | --- | 
| _listing_ | Can you list all payments made in _Pizza Hut_ restaurant? | 
| _summation_ | What is my spending on _groceries_ since June 2024? | 
| _max/min_ | _What stores did I purchase my gas at and what's the most I have paid so far?_ | 

<br>

### CODE & ARCHITECTURE

The chatbot implementation consist of a two-stage process.
| Process | Description | Outcome |
| --- | --- | --- |
| Prefilter (Stage 1) | Fetches transaction data of the inputted `user-id`, retrieved identity and language preference, then renames every transaction number category. | During chatting process, bot will have access to user-specific data only, and can address the user personally. |
| Chatting (Stage 2) | Receives user query, checks using LLM if it is within bot's ability to answer, translates user query to `params` for manual data retrieval, and formulates final answer with LLM. | Provides a detailed response to the user as well as the source data. |

User can see the `parameters` and `relevant data` used in chatting process for *LLM answer transparency*.

Illustrative take on the architecture can be seen in `documentation/product-pitch.pdf`.

<br>

### DEPLOYMENT
Try bot yourself : [https://bankingpa-ssh.streamlit.app/](https://bankingpa-ssh.streamlit.app/)

See bot in action : [trial demo]()

_This demo uses _free Gemini account_ that may limit your experience as queries that can be sent are limited._