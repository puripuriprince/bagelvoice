# Queues and Deques: Fundamental Data Structures

## Overview

This lecture will explore the Queue and Deque Abstract Data Types (ADTs), their properties, implementations, and applications. We will begin by defining the Queue ADT and its FIFO (First-In, First-Out) behavior, followed by a discussion of array-based implementations, including the concept of circular arrays to handle queue growth. We will then extend our discussion to Deques (Double-Ended Queues), which offer more flexible insertion and deletion operations.  Finally, we will examine real-world applications of these data structures, including scheduling and other algorithmic contexts.

## Introduction

Queues and Deques are fundamental data structures used extensively in computer science. They provide a way to organize and manage collections of data where the order of processing is important.  Understanding these ADTs is crucial for designing and implementing efficient algorithms for various applications.

**Learning Objectives:**

* Understand the Queue and Deque ADTs and their core operations.
* Implement Queues using arrays and the concept of circular arrays.
* Analyze the time complexity of queue operations.
* Understand the advantages and disadvantages of different queue implementations.
* Learn about the Deque ADT and its extended functionalities.
* Explore real-world applications of Queues and Deques.


## Main Content

### Chapter 1: The Queue ADT

* **Definition:** A Queue is a linear data structure that follows the FIFO principle.  Elements are added at the rear (enqueue) and removed from the front (dequeue).
* **Key Operations:**
    * `enqueue(object)`: Adds an element to the rear of the queue.
    * `dequeue()`: Removes and returns the element at the front of the queue.
    * `front()`: Returns the element at the front without removing it.
    * `size()`: Returns the number of elements in the queue.
    * `isEmpty()`: Returns true if the queue is empty, false otherwise.
* **Exceptions:** Attempting `dequeue()` or `front()` on an empty queue throws an `EmptyQueueException`.

### Chapter 2: Array-Based Queue Implementation

* **Fixed Capacity:**  Initial implementations often use a fixed-size array.
* **Circular Array:** To avoid shifting elements on dequeue, a circular array approach is used. Two indices, `f` (front) and `r` (rear), track the queue's elements within the array. The `r` index points to the next available slot.
* **Modulo Operator:**  The modulo operator (`%`) is used to wrap around the array indices, creating the circular behavior.
* **Size Calculation:** `size() = ((N - f) + r) % N`, where N is the array size.
* **Empty Condition:** `isEmpty()` is true when `f = r`.

### Chapter 3: Growable Array-Based Queue

* **Dynamic Resizing:** To overcome the fixed-size limitation, the array can be resized when full during an `enqueue()` operation.
* **Strategies:**
    * **Incremental Strategy:** Increase the array size by a fixed amount. This leads to an amortized O(n) time complexity for `enqueue()`.
    * **Doubling Strategy:** Double the array size when full. This provides an amortized O(1) time complexity for `enqueue()`.

### Chapter 4: The Deque ADT

* **Definition:** A Deque (Double-Ended Queue) is a linear data structure that allows insertions and deletions at both ends (front and rear).
* **Key Operations:**
    * `addFirst(e)`: Adds an element to the front.
    * `addLast(e)`: Adds an element to the rear.
    * `removeFirst()`: Removes and returns the element from the front.
    * `removeLast()`: Removes and returns the element from the rear.
    * `getFirst()`: Returns the front element without removing it.
    * `getLast()`: Returns the rear element without removing it.
    * `size()` and `isEmpty()`: Similar to the Queue ADT.

### Chapter 5: Queue and Deque in Java

* **Queue Interface:** Java provides a `Queue<E>` interface, but it doesn't have a direct corresponding built-in class for our specific Queue ADT implementation.
* **Deque Interface:**  Java's `Deque<E>` interface provides the functionality of a double-ended queue.
* **Implementation:**  Various classes like `ArrayDeque` and `LinkedList` implement the `Deque` interface.


## Practical Applications

* **Round Robin Schedulers:** Queues are used to manage processes waiting for a shared resource (e.g., CPU, printer).  The round-robin algorithm dequeues a process, allocates a time slice for it, and then enqueues it back to the queue.
* **Waiting Lists and Bureaucracy:** Queues naturally model real-world scenarios like waiting lists, where people are served in the order they arrive.
* **Auxiliary Data Structure:** Queues are often used within algorithms like Breadth-First Search (BFS) for graph traversal.
* **Component of Other Data Structures:** Queues can be used as building blocks for implementing other data structures.


## Conclusion

We have explored the Queue and Deque ADTs, their implementations using arrays, and their applications.  The circular array implementation provides an efficient way to manage queue operations with amortized constant time complexity. Deques extend the functionality of queues by allowing insertions and deletions at both ends.  These data structures are essential tools for computer scientists and software engineers, providing efficient solutions for various problems involving ordered data processing.  Understanding their properties and implementations is crucial for designing and analyzing algorithms in various domains.
