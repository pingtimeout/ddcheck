# DDCheck

To run the DDCheck application, use the following command:

```bash
poetry run streamlit run ddcheck/main.py
```

To rebuild the Docker image, run the following command:

```bash
docker build -t gcr.io/dremio-1093/ddcheck:latest .
```

To publish the Docker image, run the following command:

```bash
docker push gcr.io/dremio-1093/ddcheck:latest
```
