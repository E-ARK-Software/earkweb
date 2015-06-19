var demoLanguage = {

	// Set a unique name for the language
	languageName: "informationPackageProcessingLanguage",

	// inputEx fields for pipes properties
	propertiesFields: [
		// default fields (the "name" field is required by the WiringEditor):
		{"type": "string", inputParams: {"name": "name", label: "Title", typeInvite: "Enter a title" } },
		{"type": "text", inputParams: {"name": "description", label: "Description", cols: 30} },

		// Additional fields
		{"type": "boolean", inputParams: {"name": "isTest", value: true, label: "Test"}},
		{"type": "select", inputParams: {"name": "category", label: "Category", selectValues: ["Demo", "Test", "Other"]} }
	],

	// List of node types definition
	modules: [

	{
	      "name": "XML Validation",
	      "container": {
	   		"xtype": "WireIt.FormContainer",
	   		"title": "METS XML Validation",
	   		"icon": "/static/earkweb/workflow/wireit/res/icons/valid-xml.png",
	   		"collapsible": true,
			"drawingMethod": "arrows",
	   		"fields": [
				{"type":"boolean", "inputParams": {"label": "check well-formed", "name": "well-formed"}},
				{"type":"boolean", "inputParams": {"label": "check valid ?", "name": "valid"}}
	   		],
			"terminals": [
                             {"name": "_INPUT", "direction": [0,0], "offsetPosition": {"left": 160, "top": -13 },"ddConfig": {"type": "input","allowedTypes": ["output"]}, "nMaxWires": 1,  "drawingMethod": "arrows" },
                             {"name": "_OUTPUT", "direction": [0,0], "offsetPosition": {"left": 160, "bottom": -13 },"ddConfig": {"type": "output","allowedTypes": ["input"]}}
                         ],

	   		"legend": "METS XML Validation",
			"drawingMethod": "arrows"
	   	}
	   },
	   {
	      "name": "SIP Extraction",
	      "container": {
	   		"xtype": "WireIt.FormContainer",
	   		"title": "SIP Extraction",
	   		"icon": "/static/earkweb/workflow/wireit/res/icons/unzip.png",
	   		"collapsible": true,
	   		"fields": [
	   			{inputParams: {label: 'Working directory', name: 'working_dir', required: true, value:'/home/shs/eark/' } }
	   		],
			"terminals": [
                             {"name": "_INPUT", "direction": [0,0], "offsetPosition": {"left": 160, "top": -13 },"ddConfig": {"type": "input","allowedTypes": ["output"]}, "nMaxWires": 1 },
                             {"name": "_OUTPUT", "direction": [0,0], "offsetPosition": {"left": 160, "bottom": -13 },"ddConfig": {"type": "output","allowedTypes": ["input"]}}
                         ],
	   		"legend": "METS XML Validation"
	   	}
	   },
		{
	      "name": "File format identification",
	      "container": {
	   		"xtype": "WireIt.FormContainer",
	   		"title": "SIP Extraction",
	   		"icon": "/static/earkweb/workflow/wireit/res/icons/fid.png",
	   		"collapsible": true,
	   		"fields": [
	   			{inputParams: {label: 'Working directory', name: 'working_dir', required: true, value:'/home/shs/eark/' } }
	   		],
			"terminals": [
                             {"name": "_INPUT", "direction": [0,0], "offsetPosition": {"left": 160, "top": -13 },"ddConfig": {"type": "input","allowedTypes": ["output"]}, "nMaxWires": 1 },
                             {"name": "_OUTPUT", "direction": [0,0], "offsetPosition": {"left": 160, "bottom": -13 },"ddConfig": {"type": "output","allowedTypes": ["input"]}}
                         ],
	   		"legend": "METS XML Validation"
	   	}
	   },

			]

};
