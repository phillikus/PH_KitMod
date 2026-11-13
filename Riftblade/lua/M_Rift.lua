function RBRESC(effect, target)
	local caster = EEex_GameObject_Get(effect.m_sourceId)
	if not caster then
		return
	end
	if not caster.m_pArea or not target.m_pArea then
		return
	end

	local x, y = EEex_Area_GetNearestOpenPosition(
		target.m_pArea,
		caster.m_pos.x,
		caster.m_pos.y,
		true
	)
	if not x or not y then
		return
	end

    target:virtual_ClearActions(false)
	local response = string.format("JumpToPoint([%d.%d])", x, y)
	EEex_Action_QueueResponseStringOnAIBase(response, target)
end

function RBEXCH(effect, target)
	local caster = EEex_GameObject_Get(effect.m_sourceId)
	if not caster or not caster.m_pArea or not target.m_pArea then
		return
	end

	local casterX, casterY = caster.m_pos.x, caster.m_pos.y
	local targetX, targetY = target.m_pos.x, target.m_pos.y

    target:virtual_ClearActions(false)

	EEex_Action_QueueResponseStringOnAIBase(
		string.format("JumpToPoint([%d.%d])", casterX, casterY),
		target
	)
	EEex_Action_QueueResponseStringOnAIBase(
		string.format("JumpToPoint([%d.%d])", targetX, targetY),
		caster
	)
end
