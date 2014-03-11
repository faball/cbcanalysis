package ch.cern.web.bristol.cbcteststand.client;

import com.google.gwt.core.client.GWT;
import com.google.gwt.core.client.EntryPoint;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Label;
import com.google.gwtjsonrpc.common.AsyncCallback;
import com.google.gwt.user.client.rpc.ServiceDefTarget;

public class ProgramEntryPoint implements EntryPoint
{
	private GlibControlService service_ = GWT.create(GlibControlService.class);
	private Label echo_ = new Label();
	
	@Override
	public void onModuleLoad()
	{
		RootPanel.get("LoadingPlaceholder").setVisible(false);
		
		echo_.setText("Initialising...");
		
		((ServiceDefTarget) service_).setServiceEntryPoint(GWT.getModuleBaseURL() + "../cbcTestStand/services/GlibControlProxy.py");

		service_.connectedCBCNames( new String[0], new AsyncCallback<String[]>() {
			public void onSuccess( String[] result)
			{
				String message="Result is ";
				for( String cbcName : result ) message+=cbcName+", ";
				echo_.setText(message);
			}
			public void onFailure(Throwable why)
			{
				echo_.setText("Failed due to "+why.getMessage());
			}
		});

		// Create a button widget
		final Button button = new Button();
		button.setText("Click me!");
		button.addClickHandler(
			new ClickHandler()
			{
				@Override
				public void onClick(ClickEvent event)
				{
					button.setText("Hello, world! ("+GWT.getModuleBaseURL() + ")");
				}
			});
		RootPanel.get().add(button);
		RootPanel.get().add(echo_);
	}
}