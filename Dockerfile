# 
FROM python:3.11.4

# 
EXPOSE 3978
WORKDIR /


# 
COPY ./requirements.txt /requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./ /
# 
CMD ["python", "vertex_bot/app.py"]