目标：
    前端发送一个post请求，给container_manager，目前刘浩给的请求中指定了要创建container的机器的ip地址，因此leader接到请求把任务分发给对应的机器
slaver, slaver拿到请求后创建container， 然后返回创建的结果， 也就是给一个post请求，自动地在对应的服务器上创建了container。

    目前我测试一下，这个流程基本可以走下来， 但流程中尚存在的问题：

	1：在创建container的时候之前的权限问题（像是权限问题）没有解决，导致container虽然能够创建完成， 但是环境是有问题的
	2：程序判断创建container是否创建成功的方法没有封装完善。



此外：
	
	通过leader自动筛选机器去创建container中尚未解决：
	    筛选的方法尚未完成。
	这一种情况和刘浩商量后想在第二版中完成或者把制定ip自动创建完成后去实现。
		
	