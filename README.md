# calculate-agents
This project implements some clusters model for calculate task. Main point is design logic of agents communication.


## Dependecies

* Python 3.11
* FastAPI >= 0.103.x

## Build

```bash
git clone https://github.com/timofeevAS/calculate-agents
cd ./calculate-agents
python -m venv venv
cd ./.venv/Scripts
./activate
cd ../..
```

## Run

```bash
uvicorn main:app --reload    
```

Your application can available [127.0.0.1:8000](http://127.0.0.1:8000/docs)
