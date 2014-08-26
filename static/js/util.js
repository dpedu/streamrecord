function getValidator(name) {
	if(validators[name]) {
		return validators[name]
	}
	return null
}
function validate(form) {
	validator = getValidator(form.data("validation"))
	if(validator) {
		answer = validator(form)
		if(typeof answer=="object") {
			ui._modal(form.find(".modal"), ENV.list({messages:answer}))
			return false
		}
		return answer
	}
	return true
}