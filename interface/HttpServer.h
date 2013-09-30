#ifndef XtalDAQ_OnlineCBCAnalyser_interface_HttpServer_h
#define XtalDAQ_OnlineCBCAnalyser_interface_HttpServer_h

#include <string>
#include <vector>
#include <memory>

namespace httpserver
{
	/** @brief Very simple HTTP server copied from the boost asio examples
	 *
	 * http://www.boost.org/doc/libs/1_54_0/doc/html/boost_asio/examples/cpp11_examples.html
	 * Modified so that the start call starts the io_service running in a new thread so that
	 * it doesn't block.
	 *
	 * @author Mark Grimes (mark.grimes@bristol.ac.uk) but functionality from site above.
	 * @date 22/Sep/2013
	 */
	class HttpServer
	{
	public:
		/** @brief HTTP headers that will be in the request and your reply
		 */
		struct Header
		{
			std::string name;
			std::string value;
		};

		/** @brief The structure that your handler needs to feel to indicate the response.
		 */
		struct Reply
		{
			enum StatusType
			{
				ok = 200,
				created = 201,
				accepted = 202,
				no_content = 204,
				multiple_choices = 300,
				moved_permanently = 301,
				moved_temporarily = 302,
				not_modified = 304,
				bad_request = 400,
				unauthorized = 401,
				forbidden = 403,
				not_found = 404,
				internal_server_error = 500,
				not_implemented = 501,
				bad_gateway = 502,
				service_unavailable = 503
			} status;

			std::vector<Header> headers;
			std::string content;

			/// Get a stock reply.
			static Reply stockReply( StatusType status );
		};

		/** @brief The description of the request that your handler needs to respond to.
		 */
		struct Request
		{
			std::string method;
			std::string uri;
			int http_version_major;
			int http_version_minor;
			std::vector<Header> headers;
		};

		/** @brief The interface that needs to be subclassed and passed to the HttpServer constructor.
		 *
		 * This is the interface that you need to subclass and then pass an instance of to the
		 * HttpServer constructor so that it knows how to handel the HTTP requests.
		 */
		class IRequestHandler
		{
		public:
			virtual ~IRequestHandler() {}
			virtual void handleRequest( const httpserver::HttpServer::Request& request, httpserver::HttpServer::Reply& reply ) = 0;
		};

	public:
		HttpServer( IRequestHandler& requestHandler );
		~HttpServer();
		void start( const std::string& address, const std::string& port );
		void stop();
	private:
		std::unique_ptr<class HttpServerPrivateMembers> pImple;
	};

} // namespace httpserver

#endif
