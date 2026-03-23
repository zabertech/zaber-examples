<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="26008000">
	<Property Name="CCSymbols" Type="Str"></Property>
	<Property Name="NI.LV.All.SaveVersion" Type="Str">26.0</Property>
	<Property Name="NI.LV.All.SourceOnly" Type="Bool">true</Property>
	<Property Name="NI.Project.Description" Type="Str"></Property>
	<Item Name="My Computer" Type="My Computer">
		<Property Name="server.app.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.control.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.tcp.enabled" Type="Bool">false</Property>
		<Property Name="server.tcp.port" Type="Int">0</Property>
		<Property Name="server.tcp.serviceName" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.tcp.serviceName.default" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.vi.callsEnabled" Type="Bool">true</Property>
		<Property Name="server.vi.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="specify.custom.address" Type="Bool">false</Property>
		<Item Name="basic.vi" Type="VI" URL="../basic.vi"/>
		<Item Name="Newtonsoft.Json.Bson.dll" Type="Document" URL="../dlls/Newtonsoft.Json.Bson.dll"/>
		<Item Name="Newtonsoft.Json.dll" Type="Document" URL="../dlls/Newtonsoft.Json.dll"/>
		<Item Name="zaber-motion-core-windows-386.dll" Type="Document" URL="../dlls/zaber-motion-core-windows-386.dll"/>
		<Item Name="zaber-motion-core-windows-amd64.dll" Type="Document" URL="../dlls/zaber-motion-core-windows-amd64.dll"/>
		<Item Name="zaber-motion-core-windows-arm64.dll" Type="Document" URL="../dlls/zaber-motion-core-windows-arm64.dll"/>
		<Item Name="Zaber.Motion.dll" Type="Document" URL="../dlls/Zaber.Motion.dll"/>
		<Item Name="Dependencies" Type="Dependencies"/>
		<Item Name="Build Specifications" Type="Build"/>
	</Item>
</Project>
