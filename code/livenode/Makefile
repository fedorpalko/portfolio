CC = g++
CFLAGS = -Wall -std=c++17 -I./include
LDFLAGS = -lcurl

TARGET = livenode_exec
SRC = src/main.cpp

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET) $(LDFLAGS)

clean:
	rm -f $(TARGET)
