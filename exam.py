
#second largest
def sort(a):
    if a[0] > a[1]:
        first = a[0]
        second = a[1]
    else:
        first = a[1]
        second = a[0]

    for i in range(2, len(a)):
        if a[i] > second:
            if a[i] >= first:
                first, second = a[i], first
            else:
                second = a[i]
    print(second)

an = [4,5,81,78,0,2,4]
sort(an)


#sort
li = [2.3, 67.8, 9, 21.9, 45, 9, 0, 45.6, 3, 89]
def sorter(listss):
    l = listss
    for i in range(0, len(l)):
        for j in range(i+1, len(l)):
            if l[i]>l[j]:
                l[i], l[j] = l[j], l[i]

    print(l)
sorter(li)


# def second_largest(numbers):
#     new_list = numbers
#     first = new_list[0]
#     print(first)
#     for i in new_list:
#         if i > first:
#             first = i
#     new_list.remove(first)
#     print(first)
#     second = new_list[0]
#     for i in new_list:
#         if i > second:
#             second = i
#     print(second)

# listi = [4,5,81,8,0,2,4]
# second_largest(listi)
# print(listi)






# print(listi)        
# print(a)
    # a is the list of items, and the number of entries it contains is # len(a).
    # You may assume that len(a) >= 1.
    # YOU FILL IN THE BODY OF THIS FUNCTION.