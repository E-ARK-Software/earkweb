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
		{"type": "select", inputParams: {"name": "category", label: "Category", selectValues: ["SIP to AIP", "AIP to DIP", "IP to IP"]} }
	],

	// List of node types definition
	modules: [

	{% for wdef in workflow_definitions %}
	{% autoescape off %}
    {{ wdef.model_definition }}
	{% endautoescape %}

    {% endfor %}

	]

};
