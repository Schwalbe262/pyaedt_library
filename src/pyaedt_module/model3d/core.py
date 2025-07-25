class Core :

    def __init__(self, design) :
        self.design = design
    
    def __getattr__(self, name):
        return getattr(self.design, name)
    

    def create_coretype_core(self, name="core", **kwargs) :
        """
        코어 타입의 코어를 생성합니다.
        
        Parameters:
            name (str): 코어의 이름
            **kwargs:
                w1 (str): 코어의 너비
                l1_leg (str): 코어의 다리 길이
                l1_top (str): 코어의 상단 길이
                l2 (str): 코어의 길이
                h1 (str): 코어의 높이
                mat (str): 코어의 재질
                coreloss (bool): 코어 손실 활성화 여부
                
        Returns:
            object: 생성된 코어 객체
        """

        """
        사용 예시

        core_params = {
            "w1": "w1", # 변수가 아니라 값을 넣어도 됨
            "l1_leg": "l1",
            "l1_top": "l1",
            "l2": "l2",
            "h1": "h1",
            "mat": "ferrite"
        }

        self.core = modeler.create_coretype_core(name="Core", **core_params)
        
        """


        # variable setting
        core_w1 = kwargs.get("w1", "60mm") # core_w1
        core_l1_leg = kwargs.get("l1_leg", "25mm") # core_l1_leg
        core_l1_top = kwargs.get("l1_top", "25mm") # core_l1_top
        core_l2 = kwargs.get("l2", "80mm") # core_l2
        core_h1 = kwargs.get("h1", "80mm") # core_h1

        material = kwargs.get("mat", "ferrite")
        coreloss = kwargs.get("coreloss", False)

        # make core (main part)
        origin = [f"-({core_w1})/2", f"-(2*{core_l1_leg} + {core_l2})/2", f"-(2*{core_l1_top} + {core_h1})/2"]
        dimension = [f"({core_w1})", f"(2*{core_l1_leg} + {core_l2})", f"(2*{core_l1_top} + {core_h1})"]
        core_base = self.design.modeler.create_box(
            origin = origin,
            sizes = dimension,
            name = name,
            material = material
        )

        # make core (sub part)
        origin = [f"-({core_w1})/2", f"-({core_l2})/2", f"-({core_h1})/2"]
        dimension = [f"({core_w1})", f"({core_l2})", f"({core_h1})"]
        core_sub = self.design.modeler.create_box(
            origin = origin,
            sizes = dimension,
            name = f'{name}_sub',
            material = material
        )


        # subtract core
        blank_list = [core_base.name]
        tool_list = [core_sub.name]

        self.design.modeler.subtract(
            blank_list = blank_list,
            tool_list = tool_list,
            keep_originals = False
        )

        core_base.transparency = 0

        # fillet
        # if kwargs['fillet'] == True :
        #     fillet_edge = [edge for edge in core_base.edges if edge.midpoint[0] == 0]

        if coreloss == True :
            self.design.set_core_losses(assignment=core_base, core_loss_on_field=True)

        return core_base
    



    def create_shelltype_core(self, name="core", **kwargs) :
        """
        코어 타입의 코어를 생성합니다.
        
        Parameters:
            name (str): 코어의 이름
            **kwargs:
                w1 (str): 코어의 너비
                l1_center (str): 코어의 중심 길이
                l1_side (str): 코어의 사이드 길이
                l1_top (str): 코어의 상단 길이
                l2 (str): 코어의 길이
                h1 (str): 코어의 높이
                mat (str): 코어의 재질
                coreloss (bool): 코어 손실 활성화 여부
                
        Returns:
            object: 생성된 코어 객체
        """

        """
        사용 예시

        core_params = {
            "w1": "w1", # 변수가 아니라 값을 넣어도 됨
            "l1_leg": "l1",
            "l1_top": "l1",
            "l2": "l2",
            "h1": "h1",
            "mat": "ferrite"
        }

        self.core = modeler.create_coretype_core(name="Core", **core_params)
        
        """


        # variable setting
        core_w1 = kwargs.get("w1", "60mm") # core_w1
        core_l1_center = kwargs.get("l1_center", "50mm") # core_l1_leg
        core_l1_side = kwargs.get("l1_side", "25mm") # core_l1_leg
        core_l1_top = kwargs.get("l1_top", "25mm") # core_l1_top
        core_l2 = kwargs.get("l2", "80mm") # core_l2
        core_h1 = kwargs.get("h1", "80mm") # core_h1

        material = kwargs.get("mat", "ferrite")
        coreloss = kwargs.get("coreloss", False)

        # make core (main part)
        origin = [f"-({core_w1})/2", f"-(2*{core_l1_side} + {core_l1_center} + 2*{core_l2})/2", f"-(2*{core_l1_top} + {core_h1})/2"]
        dimension = [f"({core_w1})", f"(2*{core_l1_side} + {core_l1_center} + 2*{core_l2})", f"(2*{core_l1_top} + {core_h1})"]
        core_base = self.design.modeler.create_box(
            origin = origin,
            sizes = dimension,
            name = name,
            material = material
        )

        # make core (sub part)
        origin = [f"-({core_w1})/2", f"-({core_l1_center})/2", f"-({core_h1})/2"]
        dimension = [f"({core_w1})", f"-({core_l2})", f"({core_h1})"]
        core_sub1 = self.design.modeler.create_box(
            origin = origin,
            sizes = dimension,
            name = f'{name}_sub1',
            material = material
        )

        origin = [f"-({core_w1})/2", f"({core_l1_center})/2", f"-({core_h1})/2"]
        dimension = [f"({core_w1})", f"({core_l2})", f"({core_h1})"]
        core_sub2 = self.design.modeler.create_box(
            origin = origin,
            sizes = dimension,
            name = f'{name}_sub2',
            material = material
        )



        # subtract core
        blank_list = [core_base.name]
        tool_list = [core_sub1.name, core_sub2.name]

        self.design.modeler.subtract(
            blank_list = blank_list,
            tool_list = tool_list,
            keep_originals = False
        )

        core_base.transparency = 0

        # fillet
        # if kwargs['fillet'] == True :
        #     fillet_edge = [edge for edge in core_base.edges if edge.midpoint[0] == 0]

        if coreloss == True :
            self.design.set_core_losses(assignment=core_base, core_loss_on_field=True)

        return core_base