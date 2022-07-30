//创建vue对象
let vm = new Vue({
    el: '#app',//通过ID选择器找到绑定的HTML内容
    //修改vue读取变量的语法
    delimiters:['[[',']]'],

    data:{//数据对象
        // V-model
        username : '',
        password : '',
        password2 : '',
        mobile : '',
        allow : '',
        img_code_url:'',
        //V-show
        error_name : false,
        error_password :false,
        error_password2 :false,
        error_mobile : false,
        error_allow : false,

        // error_message
        error_name_message : '',
        error_mobile_message : '',
    },
    mounted(){//页面加载完会被调用
        //生成图形验证码
        this.generate_image_code();
    },
    methods:{//定义和实现事件方法
        //生成图形验证码的方法：封装的思想，代码复用
        generate_image_code(){
            this.uuid = generateUUID();
            this.img_code_url = '/image_codes/' + this.uuid + '/';

        },
        //效验用户名
        check_username() {
            // 用户名是5-20个字符，[a-zA-Z0-9_-]
            //定义正则
            let re = /^[a-zA-Z0-9_-]{5,20}$/;
            //使用正则匹配用户数据
            if(re.test(this.username)){
                //匹配成功，不显示错误提示信息
                this.error_name = false;
            }else{
                //匹配失败，展示错误提示信息
                this.error_name_message = '请输入5-20个字符的用户名';
                this.error_name = true;
            }
            //判断用户是否重复注册
            if(this.error_name == false){//只有当用户输入的用户名满足条件时才回去判断
                let url = '/usernames/' + this.username + '/count/';
                axios.get(url,{//请求头
                    responseType : 'json'
                }).then(response =>{
                        if(response.data.count == 1){
                            //用户名已存在
                            this.error_name_message = '用户名已存在!'
                            this.error_name = true;
                        }else{
                             //用户名不存在
                            this.error_name = false;
                        }
                    }).catch(error =>{
                            console.log(error.response);
                    })
            }
        },
        //效验密码
        check_password() {
            let re = /^[0-9A-Za-z]{8,20}$/;
            if(re.test(this.password)){
                this.error_password = false;
            }else{
                this.error_password = true;
            }
        },
        //效验确认密码
        check_password2() {
            if(this.password != this.password2){
                this.error_password2 = true;
            }else{
                this.error_password2 =false;
            }
        },
        //效验手机号
        check_mobile() {
            let re = /^1[3-9]\d{9}$/;
            if(re.test(this.mobile)){
                this.error_mobile = false;
            }else {
                this.error_mobile_message = '您输入的手机号格式不正确';
                this.error_mobile = true;
            }
        },
        //效验是否勾选协议
        check_allow() {
            if(!this.allow){
                this.error_allow = true;
            }else{
                this.error_allow = false;
            }
        },
        //监听表单提交事件
        on_submit() {
            this.check_username();
            this.check_password();
            this.check_password2();
            this.check_mobile();
            this.check_allow();

            if(this.error_name == true || this.error_password == true || this.error_password == true
                || this.error_password2 == true || this .error_mobile == true || this.error_allow == true){
                //效验不通过，禁用提交表单
                window.event.returnValue =false;
            }
        }
    },
});