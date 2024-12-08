Задание

Вам предстоит написать python-скрипт, который будет взаимодействовать с Apache
Kafka следующим образом: 
1. При исполнении команды
python3 main.py produce --message 'Hello World!' --topic 'hello_topic'
--kafka 'ip:port' Скрипт должен класть сообщение, указанное в параметре message
в топик, указанный в параметре topic, в указанный инстанс Kafka.
2. При исполнении команды:
   python3 main.py consume --topic 'hello_topic' --kafka 'ip:port' Скрипт
   должен подписаться на топик, указанный в параметре 'topic' и в бесконечном
   цикле выводить полученные сообщения.
3. Полученный скрипт нужно упаковать в docker образ. В качестве entrypoint
   указать скрипт.
4. Написать docker-compose файл, с помощью которого будут разворачиваться
   Apache Kafka 
___________________________________________________________________________

Инструкция для запуска скрипта:

1. Скачать репозиторий Task_1
2. Переместиться в директорию Task_1
3. Запустить docker-compose: docker-compose up
4. Открыть новый терминал и переместиться в директорию Task_1/main
5. Запустить скрипт в режиме Consume:
   * python3 main.py --mode "consume" --topic "hello_topic" --kafka "localhost:29092"
6. Открыть новый терминал и переместиться в директорию Task_1/main
7. Запустить скрипт в режиме Produce:
   * python3 main.py --mode "produce" --message "Hello World!" --topic "hello_topic" --kafka "localhost:29092"
8. Перейти обратно в терминал Consume и убедиться, что сообщения отображаются
9. Если необходимо отравлять/принимать сообщения непосредственно из контейнера "client" в docker,
то параметр --kafka необходимо заменить на "broker:9092":
   * python3 main.py --mode "consume" --topic "hello_topic" --kafka "broker:9092"
   * python3 main.py --mode "produce" --message "Hello World!" --topic "hello_topic" --kafka "broker:9092" 
