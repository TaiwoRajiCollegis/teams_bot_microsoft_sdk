# 
FROM python:3.11.9

# 
EXPOSE 3978
WORKDIR /


# 
COPY ./requirements.txt /requirements.txt

# 
RUN pip install -r requirements.txt

COPY ./ /
# 
CMD ["python", "vertex_bot/app.py"]